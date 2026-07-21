function RunAnyCommandAndPause {
  
  param(
    [string]$Command
  )
  # print command
  Write-Host $Command
  Invoke-Expression $command

  Read-Host "Press enter key to continue"
}

# 管理虚拟机函数，接受名字作为参数
function ManageVM($VMName) {
  $VM = Get-VM -Name $VMName
  do {
    Clear-Host

    Write-Host "============================"
    Write-Host "Manage: $VMName`t[$($VM.State)]"
    Write-Host "============================"

    $VM | Format-Table
    # 提供以下几个选项，用于管理：启动、停止
    Write-Host "1. Start"
    Write-Host "2. Stop"
    Write-Host "3. Connect"
    Write-Host "4. Expose Virtualization Extensions"
    Write-Host "----------------------------"
    Write-Host "x. Back"
    Write-Host "h. Home"
    
    $choice = Read-Host "Select an option"
    
    switch ($choice) {
      1 { 
        RunAnyCommandAndPause "Start-VM -Name $VMName "
      }
      2 { 
        RunAnyCommandAndPause "Stop-VM -Name $VMName "
      }
      4 {
        RunAnyCommandAndPause "Set-VMProcessor -VMName $VMName -ExposeVirtualizationExtensions `$true"
      }
      "x" { return -1 }
      "h" { return -2 }
      default { Write-Host "Invalid Choice" }
    }
  } while ($true)
}

function ListVMs() {
  Write-Host "Loading list..."
  $list = Get-VM
  do {
    Clear-Host

    Write-Host "============================"
    Write-Host "Hyper-V Virtual Machines"
    Write-Host "============================"

    # 原样打印 Get-VM 美化表格
    $list | Format-Table

    # 把输出的列表转换成选项，可供用户选择
    $options = @()
    foreach ($VM in $list) {
      # 打印 序号、名字
      Write-Host "$($list.IndexOf($VM) + 1). $($VM.Name)`t[$($VM.State)]"
      $options += $VM.Name
    }
    Write-Host "x. Back"

    # 输出为数字选项，并且让用户选择
    $choice = Read-Host "Select a VM to manage"

    if ($choice -eq "x") {
      return -1
    }
  
    $VMName = $options[$choice - 1]
  
    # 如果$VMName 为空，提示错误
    if ([string]::IsNullOrEmpty($VMName)) {
      Write-Host "Invalid Choice"
    }
    else {
      $result = ManageVM($VMName)
      if ($result -eq -2) {
        return -2
      }
    }
  } while ($true)
}

function GetNetworkAdapters() {
  RunAnyCommandAndPause "Get-VMNetworkAdapter -All  | Format-Table"
}


function ManageSwitch($name) {
  do {
    Clear-Host

    Write-Host "============================"
    Write-Host "Manage Switch: $name"
    Write-Host "============================"

    Write-Host "d. Delete"
    Write-Host "x. Back"
    Write-Host "h. Home"
    
    $choice = Read-Host "Select an option"
    
    switch ($choice) {
      "d" { 
        RunAnyCommandAndPause "Remove-VMSwitch -Name $name"
        # TODO: fix
        return 0
      }
      "x" { return -1 }
      "h" { return -2 }
      default { Write-Host "Invalid Choice" }
    }
  } while ($true)
}

function AddInternalSwitchWithStaticIP() {
  $name = Read-Host "Input Switch Name"
  if ([string]::IsNullOrEmpty($name)) {
    Write-Host "Invalid Name"
    return
  }
  $ip = Read-Host "Input IPAddress (eg: 192.168.56.1)"
  if ([string]::IsNullOrEmpty($ip)) {
    Write-Host "Invalid IP"
    return
  }
  $prefix = Read-Host "Input Prefix (eg: 24)"
  if ([string]::IsNullOrEmpty($prefix)) {
    Write-Host "Invalid Prefix"
    return
  }
  Write-Host "Adding, Please wait..."

  # 创建虚拟交换机，名为“NAT_DHCP”
  New-VMSwitch -SwitchName $name -SwitchType Internal
  # 获取虚拟交换机的ifindex，并赋值到变量中
  $ifindex = Get-NetAdapter -Name "vEthernet ($name)" | Select-Object -ExpandProperty 'ifIndex'
  # 在虚拟交换机上设置固定IP，用于网关IP
  New-NetIPAddress -IPAddress $ip -PrefixLength $prefix -InterfaceIndex $ifindex
}

function ListSwitches() {
  Write-Host "Loading Switches..."
  $list = Get-VMSwitch
  do {
    Clear-Host

    Write-Host "============================"
    Write-Host "Switch Management"
    Write-Host "============================"
    
    $i = 1
    foreach ($item in $list) {
      # Write-Host "$i. $($item.Name)`t[$($item.SwitchType)]"
      Write-Host "$i. $($item.Name)"
      $i++
    }

    Write-Host "----------------------------"
    Write-Host "a. Add Internal Switch With Static IP"
    Write-Host "x. Back"
    $choice = Read-Host "Select a Switch to manage"
    if ($choice -eq "x") {
      return -1
    }

    if ($choice -eq "a") {
      AddInternalSwitchWithStaticIP
      Write-Host "Loading Switches..."
      $list = Get-VMSwitch
      continue
    } 
    
    $SwitchName = $list[$choice - 1].Name
    # RunAnyCommandAndPause "Get-VMNetworkAdapter -ManagementOS -SwitchName $SwitchName | Format-Table"
    if ([string]::IsNullOrEmpty($SwitchName)) {
      Write-Host "Invalid Choice"
      Read-Host "Press enter key to continue"
    }
    else {
      $result = ManageSwitch($SwitchName)
      if ($result -eq -2) {
        return -2
      } 
      elseif ($result -eq 0) {
        Write-Host "Loading Switches..."
        $list = Get-VMSwitch
      }
    }


  } while ($true)
}


function ManageNat($name) {
  do {
    Clear-Host

    Write-Host "============================"
    Write-Host "Manage Nat: $name"
    Write-Host "============================"

    Write-Host "d. Delete"
    Write-Host "x. Back"
    Write-Host "h. Home"
    
    $choice = Read-Host "Select an option"
    
    switch ($choice) {
      "d" { 
        RunAnyCommandAndPause "Remove-NetNat -Name $name"
        return 0
      }
      "x" { return -1 }
      "h" { return -2 }
      default { Write-Host "Invalid Choice" }
    }
  } while ($true)
}

function AddNat() {
  $name = Read-Host "Input Nat Name"
  $ipPrefix = Read-Host "Input InternalIPInterfaceAddressPrefix (eg: 192.168.56.0/24)"
  RunAnyCommandAndPause "New-NetNat -Name $name -InternalIPInterfaceAddressPrefix $ipPrefix"
}


function ListNats() {
  Write-Host "Loading..."
  $list = Get-NetNat
  do {
    Clear-Host

    Write-Host "============================"
    Write-Host "NetNat Management"
    Write-Host "============================"
    
    
    $i = 1
    foreach ($item in $list) {
      Write-Host "$i. $($item.Name)"
      $i++
    }

    Write-Host "----------------------------"
    Write-Host "a. Add Nat"
    Write-Host "x. Back"
    $choice = Read-Host "Select a Nat to manage"
    if ($choice -eq "x") {
      return -1
    }
    
    if ($choice -eq "a") {
      AddNat
      Write-Host "Loading..."
      $list = Get-NetNat
      continue
    }
    
    $nat = $list[$choice - 1]

    if ($null -eq $nat) {
      Write-Host "Invalid Choice"
      Read-Host "Press enter key to continue"
      
    }
    else {

      $nat
      Read-Host "Press enter key to continue"

      $result = ManageNat($nat.Name)

      if ($result -eq 0) {
        Write-Host "Loading..."
        $list = Get-NetNat
        Write-Host "result: $result"
        Read-Host "Press enter key to continue"
      }
      elseif ($result -eq -2) {
        return -2
      }

    }


  } while ($true)
}

function Main() {
  do {
    Clear-Host
    Write-Host "============================"
    Write-Host "Hyper-V Management Tool"
    Write-Host "============================"

    Write-Host "1. Virtual Machine Management"
    Write-Host "2. List VM Network Adapters"
    Write-Host "3. VM Switch Management"
    Write-Host "4. NetNat Management"
    Write-Host "x. Exit"
    
    $choice = Read-Host "Please Input Number"
    
    switch ($choice) {
      1 { 
        ListVMs
      }
      2 { 
        GetNetworkAdapters
      }
      3 {
        ListSwitches
      }
      4 {
        ListNats
      }
      "x" { 
        # exit script
        return
      }
      default { 
        Write-Host "Invalid Choice" 
      }
    }
  } while ($true)
}


Main
